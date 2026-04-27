
#include <stdio.h>
#include <stdlib.h>
struct list
{
    int data;
    struct list *link;
};
typedef struct list *list;

list AddFirst(list head, int n)
{
    list p = calloc(1, sizeof(struct list));
    p->data = n;
    p->link = head;
    return p;
}
list AddLast(list head, int n)
{
    if (!head)
    {
        return AddFirst(head, n);
    }
    list r = head;
    list p = calloc(1, sizeof(struct list));
    p->data = n;
    for (; head->link; head = head->link)
        ;
    head->link = p;
    p->link = NULL;
    return r;
}
list AddElement(list head)
{
    list r = head;
    int pos;
    printf("Enter pos to add: ");
    scanf("%d", &pos);
    for (; pos && head; pos--, head = head->link)
        ;
    list p = calloc(1, sizeof(struct list));
    printf("Enter Data: ");
    int n;
    scanf("%d", &n);
    p->link = head->link;
    head->link = p;
    p->data = n;
    return r;
}
list AddFirstOcc(list head)
{
    list r = head;
    int key;
    printf("Enter the Value (add first occurance): ");
    scanf("%d", &key);
    for (; head; head = head->link)
        if (head->data == key)
            break;
    if (!head)
    {
        printf("The Give Value isn't present.\n");
        return r;
    }

    list p = calloc(1, sizeof(struct list));
    printf("Enter Data: ");
    int n;
    scanf("%d", &n);
    p->link = head->link;
    head->link = p;
    p->data = n;

    return r;
}
list RemoveFirst(list head)
{
    list p = head->link;
    free(head);
    return p;
}
list RemoveLast(list head)
{
    list p = head;
    for (; head->link->link; head = head->link)
        ;
    head->link = NULL;
    return p;
}
list RemoveElement(list head)
{
    list r = head;
    int pos;
    printf("Enter pos to Remove: ");
    scanf("%d", &pos);
    if (pos)
    {
        pos--;

        for (; pos && head; pos--, head = head->link)
            ;
        head->link = head->link->link;

        return r;
    }
    return RemoveFirst(r);
}
list RemoveFirstOcc(list head)
{
    list r = head;
    int i;
    printf("Enter the Value(remove first occurance): ");
    scanf("%d", &i);
    if (head->data == i)
        return RemoveFirst(r);
    for (; head; head = head->link)
        if (head->link->data == i)
            break;
    if (!head)
    {
        printf("The Give Value isn't present.\n");
        return r;
    }
    head->link = head->link->link;

    return r;
}
int GetElement(list head, int pos)
{
    for (; pos && head->link; pos--, head = head->link)
        ;

    if (!pos)
        return (head->data);
    printf("There isn't Element at Specific pos.\n");
    return 0;
}
list Reverse(list head)
{
    list p = NULL;
    int i;
    while (head)
    {
        i = GetElement(head, 0);
        p = AddFirst(p, i);
        head = head->link;
    }
    return p;
}
void prin(list p)
{
    for (; p; p = p->link)
        printf("%d -> ", p->data);
    printf("NULL\n");
}
list SetElement(list head)
{
    list p = head;
    int pos;
    printf("pos to set Element: ");
    scanf("%d", &pos);
    for (; pos && head->link; pos--, head = head->link)
        ;

    if (!pos)
    {
        int i;
        printf("Data: ");
        scanf("%d", &i);
        head->data = i;
        return p;
    }
    printf("There isn't  pos in List\n");
    return p;
}
list Sorti(list head, int n)
{
    if (!head)
        return AddFirst(head, n);
    list r = head;
    if (n < head->data)
        return AddFirst(r, n);
    for (; head; head = head->link)
    {
        if (!head->link)
            return AddLast(r, n);
        if (n <= head->link->data)
            break;
    }
    list p = calloc(1, sizeof(struct list));
    p->link = head->link;
    head->link = p;
    p->data = n;
    return r;
}
list Sort(list head)
{
    list r = head, p = NULL;
    int n;
    while (head)
    {
        n = GetElement(head, 0);
        p = Sorti(p, n);
        head = head->link;
    }
    return p;
}
void Recprin(list head)
{
    if (head)
    {
        printf("%d->", head->data);
        head = head->link;
        Recprin(head);
    }
    else
        printf("NULL");
}
void RecRevprin(list head)
{
    head = Reverse(head);
    if (head)
    {
        printf("%d->", head->data);
        head = head->link;
        Recprin(head);
    }
    else
        printf("NULL");
}
void RecReverse(list r, list head)
{
    static list q = NULL;
    static int i = 0;
    if (!head)
    {
        prin(q);
        return;
    }

    if (!head->link)
    {
        if (r)
        {
            q = AddLast(q, head->data);
            r = RemoveLast(r);
            head = r;
        }
    }

    if (!head->link)
    {
        q = AddLast(q, head->data);
    }
    head = head->link;

    if (head)
    {
        RecReverse(r, head);
    }
    if (!i)
    {
        prin(q);
        i = 1;
    }
    return;
}
int Count(list p)
{
    if (!p)
        return 0;
    int i;
    for (i = 0; p; i++, p = p->link)
        ;
    return i;
}
int main()
{
    list head = NULL;

    int n;
    scanf("%d", &n);

    int *arr = NULL;

    if (n > 0)
    {
        arr = (int *)malloc(n * sizeof(int));
        assert(arr != NULL);

        for (int i = 0; i < n; i++)
        {
            scanf("%d", &arr[i]);
        }

        for (int i = n - 1; i >= 0; i--)
        {
            head = AddFirst(head, arr[i]);
        }

        free(arr);
    }

    printf("Original list:\n");
    prin(head);

    printf("Count:\n");
    printf("%d\n", Count(head));

    printf("After removing first:\n");
    if (head)
        head = RemoveFirst(head);
    prin(head);

    int end_value;
    scanf("%d", &end_value);

    printf("After adding %d at end:\n", end_value);
    head = AddLast(head, end_value);
    prin(head);


    printf("After removing last:\n");
    if (head && head->link)
        head = RemoveLast(head);
    else if (head && head->link == NULL)
        head = RemoveFirst(head);
    prin(head);

    int get_pos;
    scanf("%d", &get_pos);

    printf("Element at position %d:\n", get_pos);
    if (head)
    {
        int value = GetElement(head, get_pos);
        printf("%d\n", value);
    }
    else
    {
        printf("List is empty\n");
    }


    printf("After setting element:\n");
    if (head)
        head = SetElement(head);
    prin(head);

 
    printf("After adding element at position:\n");
    if (head)
        head = AddElement(head);
    prin(head);

    printf("After removing element at position:\n");
    if (head)
        head = RemoveElement(head);
    prin(head);

    printf("After adding after first occurrence:\n");
    if (head)
        head = AddFirstOcc(head);
    prin(head);

    printf("After removing first occurrence:\n");
    if (head)
        head = RemoveFirstOcc(head);
    prin(head);

    printf("After iterative reverse:\n");
    head = Reverse(head);
    prin(head);


    printf("After sorting:\n");
    head = Sort(head);
    prin(head);

 
    printf("Recursive print:\n");
    Recprin(head);
    printf("\n");

    printf("Recursive reverse print:\n");
    RecRevprin(head);
    printf("\n");

    printf("Recursive physical reverse output:\n");
    RecReverse(head, head);

    list sorted_list = NULL;

    int sorted_n;
    scanf("%d", &sorted_n);

    int *sorted_arr = NULL;

    if (sorted_n > 0)
    {
        sorted_arr = (int *)malloc(sorted_n * sizeof(int));
        assert(sorted_arr != NULL);

        for (int i = 0; i < sorted_n; i++)
        {
            scanf("%d", &sorted_arr[i]);
        }

        for (int i = sorted_n - 1; i >= 0; i--)
        {
            sorted_list = AddFirst(sorted_list, sorted_arr[i]);
        }

        free(sorted_arr);
    }

    printf("Sorted list:\n");
    prin(sorted_list);

    int insert_value;
    scanf("%d", &insert_value);

    printf("After sorted insertion of %d:\n", insert_value);
    sorted_list = Sorti(sorted_list, insert_value);
    prin(sorted_list);

    return 0;
}